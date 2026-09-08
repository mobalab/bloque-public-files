<?php
/**
 * Plugin Name: Flamingo Ability Bridge
 */

add_action( 'wp_abilities_api_init', 'myplugin_register_flamingo_abilities' );

function myplugin_register_flamingo_abilities() {

	wp_register_ability( 'myplugin/list-flamingo-messages', array(
		'label'              => 'List Flamingo inbox messages',
		'description'        => 'Search and retrieve inquiry messages saved to Flamingo via Contact Form 7',
		'category'           => 'site',
		'input_schema'       => array(
			'type'       => 'object',
			'properties' => array(
				'search'              => array( 'type' => 'string' ),
				'contact_form'        => array( 'type' => 'string' ), // form name or ID
				'limit'               => array( 'type' => 'integer', 'default' => 20 ),
				'is_unprocessed_only' => array(
					'type'        => 'boolean',
					'default'     => false,
					'description' => 'If true, only return unprocessed inquiries (where _flamingo_process_status is not set)',
				),
			),
		),
		'output_schema'      => array(
			'type'  => 'array',
			'items' => array( 'type' => 'object' ),
		),
		'permission_callback' => function () {
			// Read-only, so require permission equivalent to a Flamingo admin
			return current_user_can( 'manage_options' );
		},
		'execute_callback'    => function ( $input ) {
			if ( ! class_exists( 'Flamingo_Inbound_Message' ) ) {
				return new WP_Error( 'flamingo_missing', 'The Flamingo plugin is not active' );
			}

			$args = array(
				'posts_per_page' => $input['limit'] ?? 20,
				's'              => $input['search'] ?? '',
				'post_status'    => 'any',
				'orderby'        => 'date',
				'order'          => 'DESC',
			);

			if ( ! empty( $input['is_unprocessed_only'] ) ) {
				$args['meta_query'] = array(
					array(
						'key'     => '_flamingo_process_status',
						'compare' => 'NOT EXISTS',
					),
				);
			}

			$messages = Flamingo_Inbound_Message::find( $args );

			$results = array();

			foreach ( $messages as $message ) {
				$results[] = array(
					'id'      => $message->id,
					'subject' => $message->subject,
					'from'    => $message->from,       // "Name <email>" format
					'name'    => $message->from_name,
					'email'   => $message->from_email,
					'date'    => $message->date,
					'fields'  => $message->fields,      // associative array of form field values
					'meta'    => $message->meta,        // IP, referer, etc.
					'spam'    => (bool) $message->spam,
				);
			}

			return $results;
		},
		'meta' => array(
			'mcp' => array(
				'public' => true, // set true to expose on the default MCP server
			),
		),
	) );

	wp_register_ability( 'myplugin/mark-flamingo-message-processed', array(
		'label'              => 'Mark a Flamingo message as processed',
		'description'        => 'Record a processed flag and timestamp on an inquiry handled by an AI agent',
		'category'           => 'site',
		'input_schema'       => array(
			'type'       => 'object',
			'properties' => array(
				'message_id' => array(
					'type'        => 'integer',
					'description' => 'Post ID of the flamingo_inbound entry',
				),
				'status'     => array(
					'type'    => 'string',
					'enum'    => array( 'done', 'failed', 'skipped' ),
					'default' => 'done',
				),
				'mark_spam'  => array(
					'type'        => 'boolean',
					'default'     => false,
					'description' => 'If true, set Flamingo\'s native spam flag (changes post_status to flamingo-spam)',
				),
			),
			'required'   => array( 'message_id' ),
		),
		'output_schema'      => array(
			'type'       => 'object',
			'properties' => array(
				'success'      => array( 'type' => 'boolean' ),
				'message_id'   => array( 'type' => 'integer' ),
				'status'       => array( 'type' => 'string' ),
				'processed_at' => array( 'type' => 'string' ),
				'spam'         => array( 'type' => 'boolean' ),
			),
		),
		'permission_callback' => function ( $input ) {
			if ( ! current_user_can( 'manage_options' ) ) {
				return false;
			}
			// Also confirm the target is an actual flamingo_inbound post at permission-check time
			$post = get_post( $input['message_id'] ?? 0 );
			if ( ! $post || Flamingo_Inbound_Message::post_type !== $post->post_type ) {
				return new WP_Error(
					'invalid_message_id',
					'No Flamingo message found with the given ID'
				);
			}
			return true;
		},
		'execute_callback'    => function ( $input ) {
			$message_id = absint( $input['message_id'] );
			$status     = $input['status'] ?? 'done';
			$mark_spam  = $input['mark_spam'] ?? false;

			// Re-check existence on the execute side too, just in case (TOCTOU guard)
			$post = get_post( $message_id );
			if ( ! $post || Flamingo_Inbound_Message::post_type !== $post->post_type ) {
				return new WP_Error(
					'invalid_message_id',
					'No Flamingo message found with the given ID'
				);
			}

			$processed_at = current_time( 'mysql' );

			update_post_meta( $message_id, '_flamingo_process_status', $status );
			update_post_meta( $message_id, '_flamingo_processed_at', $processed_at );

			if ( $mark_spam ) {
				// Instantiate directly via the constructor (not find()) to call the native method
				$flamingo_message = new Flamingo_Inbound_Message( $post );
				$flamingo_message->spam(); // internally changes post_status to flamingo-spam and saves
			}

			return array(
				'success'      => true,
				'message_id'   => $message_id,
				'status'       => $status,
				'processed_at' => $processed_at,
				'spam'         => (bool) $mark_spam,
			);
		},
		'meta' => array(
			'mcp' => array(
				// 'public' => false, // write operations are safer left private by default, exposed only on a dedicated server
				'public' => true,
			),
		),
	) );
}
