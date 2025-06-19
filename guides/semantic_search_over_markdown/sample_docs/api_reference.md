# API Reference

This API allows you to interact with the Markdown Docs Demo system — upload files, search them using natural language, and manage your document collections.

---

## 📤 POST /upload

Upload a new markdown document for semantic indexing.

**Request Body:**

```json
{
  "filename": "example.md",
  "content": "base64_encoded_content"
}
