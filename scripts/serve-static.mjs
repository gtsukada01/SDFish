import http from "node:http";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(__dirname, "..", "frontend");

const port = Number(process.env.PORT ?? 4173);

const MIME_TYPES = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".map": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".ico": "image/x-icon",
};

const server = http.createServer(async (req, res) => {
  if (!req.url) {
    res.writeHead(400);
    res.end("Bad Request");
    return;
  }

  const url = new URL(req.url, `http://localhost:${port}`);
  let relativePath = decodeURIComponent(url.pathname);
  if (relativePath.startsWith("/")) {
    relativePath = relativePath.substring(1);
  }

  if (relativePath === "") {
    relativePath = "index.html";
  } else if (relativePath.endsWith("/")) {
    relativePath = path.join(relativePath, "index.html");
  }

  const filePath = path.normalize(path.join(projectRoot, relativePath));

  if (!filePath.startsWith(projectRoot)) {
    res.writeHead(403);
    res.end("Forbidden");
    return;
  }

  const ext = path.extname(filePath);
  const contentType = MIME_TYPES[ext] ?? "application/octet-stream";

  try {
    const content = await readFile(filePath);
    res.writeHead(200, { "Content-Type": contentType });
    res.end(content);
  } catch (error) {
    // eslint-disable-next-line no-console
    const message = error instanceof Error ? error.message : String(error);
    console.warn(`[serve-static] ${url.pathname} -> 404 (${message})`);
    res.writeHead(404);
    res.end("Not Found");
  }
});

server.listen(port, () => {
  // eslint-disable-next-line no-console
  console.log(`[serve-static] Listening on http://localhost:${port}`);
});
