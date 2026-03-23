const http = require("http");
const fs = require("fs");
const path = require("path");

const host = "0.0.0.0";
const port = Number(process.env.PORT || 3000);
const rootDir = __dirname;

const contentTypes = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".txt": "text/plain; charset=utf-8",
};

function resolveRequestPath(requestUrl) {
  const requestPath = decodeURIComponent(new URL(requestUrl, "http://127.0.0.1").pathname);
  const normalizedPath = path.normalize(requestPath).replace(/^(\.\.[/\\])+/, "");
  const relativePath = normalizedPath === "/" ? "/index.html" : normalizedPath;
  return path.join(rootDir, relativePath);
}

const server = http.createServer((req, res) => {
  const filePath = resolveRequestPath(req.url || "/");
  if (!filePath.startsWith(rootDir)) {
    res.writeHead(403, { "Content-Type": "text/plain; charset=utf-8" });
    res.end("Forbidden");
    return;
  }

  fs.readFile(filePath, (error, data) => {
    if (error) {
      const statusCode = error.code === "ENOENT" ? 404 : 500;
      res.writeHead(statusCode, { "Content-Type": "text/plain; charset=utf-8" });
      res.end(statusCode === 404 ? "Not Found" : "Internal Server Error");
      return;
    }

    const extension = path.extname(filePath).toLowerCase();
    res.writeHead(200, {
      "Content-Type": contentTypes[extension] || "application/octet-stream",
    });
    res.end(data);
  });
});

server.listen(port, host, () => {
  console.log(`Static web available on http://${host}:${port}`);
});