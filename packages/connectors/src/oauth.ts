/// <reference types="node" />
import http from "node:http";

export function startOAuthProxy(port = 4321): http.Server {
  const server = http.createServer((req, res) => {
    if (req.url?.startsWith("/callback")) {
      res.writeHead(200, { "Content-Type": "text/html" });
      res.end("<h1>Conectado. Puedes cerrar esta ventana.</h1>");
      return;
    }
    res.writeHead(404);
    res.end();
  });
  server.listen(port);
  return server;
}
