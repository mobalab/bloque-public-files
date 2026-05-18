---
name: bloque-shared-file-staging
description: Upload local files from the machine running Codex into Bloque's server-side `/shared` directory using Bloque's native presigned upload/download URL tools, so Bloque-hosted stdio MCP tools can access them. Use when a task depends on local files that must become visible to MCP servers running behind Bloque, when retrieving files from `/shared`, or before invoking filesystem-backed, CLI-backed, or other server-side tools. Supports text and binary files, downloads, and directory trees that must be recreated under `/shared`.
---

# Bloque Shared File Staging

Move files between the local Codex machine and Bloque's shared server filesystem at `/shared/...` so Bloque-hosted MCP tools can operate on them.

Use Bloque's native file transfer tools for file bytes:

- Upload: call `bloque_get_upload_url` for a `/shared/...` target, then send an HTTP `PUT` with the local file bytes to the returned presigned URL.
- Download: call `bloque_get_download_url` for a `/shared/...` source, then send an HTTP `GET` to the returned presigned URL and save or inspect the bytes locally.

Use Bloque `filesystem` tools for normal server-side filesystem operations such as creating directories, listing directories, reading small text files, and verifying metadata.

## Workflow

1. Identify the local source path and the desired destination under `/shared`.
2. Inspect whether the source is a file or a directory tree.
3. Recreate destination directories on Bloque with `filesystem__create_directory`.
4. For each file, call `bloque_get_upload_url` with the final `/shared/...` path.
5. Upload the local file bytes to the returned presigned URL with HTTP `PUT`.
6. Verify the staged result with `filesystem__get_file_info`, `filesystem__list_directory`, or a targeted read when useful.
7. Hand the `/shared/...` path to the downstream Bloque-hosted MCP tool.

## Download Workflow

1. Identify the `/shared/...` source path and intended local destination or inspection need.
2. Call `bloque_get_download_url` with the `/shared/...` source path.
3. Download from the returned presigned URL with HTTP `GET`.
4. Save the bytes locally when the user needs a local file, or inspect them directly when that is enough.
5. Verify the result by checking local file size, checksum, or a short content sample as appropriate.

## Rules

- Always stage files into `/shared`, not arbitrary server paths.
- Preserve filenames unless the user asks for renaming.
- Prefer a dedicated subdirectory such as `/shared/<task-name>/` when staging multiple files.
- Verify the write before telling another tool to use the file.
- Be explicit that the staged copy is server-side and separate from the user's local file.
- Treat `/shared` as a server-shared workspace. Call out secret-bearing files and avoid staging them unless the user explicitly wants that.
- Prefer presigned upload/download URLs for transferring file bytes, including both text and binary assets.
- Use filesystem tools for directory creation, listing, metadata checks, and lightweight server-side text inspection.
- Do not route large binary transfers through base64 filesystem read/write tools when a presigned URL is available.

## Text Files

Use this flow for files such as `.txt`, `.md`, `.json`, `.yaml`, `.yml`, `.csv`, `.tsv`, `.xml`, `.html`, `.css`, `.js`, `.ts`, `.py`, `.sh`, `.sql`, and similar plaintext formats.

Preferred procedure:

1. Create the destination directory under `/shared` if needed.
2. Call `bloque_get_upload_url` for the destination file path.
3. Upload the local file with HTTP `PUT`.
4. Verify the file exists and, when useful, spot-check contents with `filesystem__read_text_file`.

## Directory Trees

When the user wants to stage a folder of text files:

1. Enumerate the local tree first.
2. Recreate the directory structure under a single `/shared/<folder>/` root.
3. Upload files one by one with `bloque_get_upload_url` plus HTTP `PUT`.
4. Summarize which files were staged and which were skipped.

## Binary Files

Use this flow for images, PDFs, Office documents, ZIP archives, audio, video, fonts, and other binary assets.

Preferred procedure:

1. Create the destination directory under `/shared` if needed.
2. Call `bloque_get_upload_url` for the destination file path.
3. Upload the local file bytes with HTTP `PUT`.
4. Verify the remote file exists and has the expected size when possible.
5. Return the final `/shared/...` path to the downstream tool.

When staging many binary files, keep a clear local-to-`/shared` path map and upload each file with its own presigned URL.

## Path Conventions

- For a single file, prefer `/shared/<original-name>`.
- For grouped work, prefer `/shared/<task-or-project>/<relative-path>`.
- Avoid spaces in new directory names unless the user already relies on them.
- Keep the final staged path easy to paste into subsequent tool calls.

## Verification

After staging:

1. Confirm the destination directory exists.
2. Confirm the file exists with nonzero size when appropriate.
3. For text files, optionally compare a short prefix or line count against the local source.
4. For binary files, optionally compare byte size or checksum against the local source.
5. Return the exact `/shared/...` path that downstream tools should use.

## Example Triggers

- "Copy `notes.md` into Bloque so the server-side tool can read it."
- "Stage this local config folder into `/shared` before running the CLI MCP tool."
- "Make my local SQL files available to the stdio server behind Bloque."
- "Upload this prompt template to Bloque shared storage so another MCP can process it."
- "Download `/shared/report.pdf` from Bloque so I can inspect it locally."

## Handoff

When the staging step is complete, report:

- The local source path.
- The final `/shared/...` destination.
- Any files skipped.
- Any notable handling details such as text vs binary transfer.
