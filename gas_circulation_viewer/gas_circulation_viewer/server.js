const http = require('http');
const fs   = require('fs');
const path = require('path');
const os   = require('os');

const PORT   = 3031;
const HOST   = '0.0.0.0';
const PUBLIC = path.join(__dirname, '..');

const MIME = {
    '.html' : 'text/html; charset=utf-8',
    '.js'   : 'text/javascript',
    '.mjs'  : 'text/javascript',
    '.css'  : 'text/css',
    '.json' : 'application/json',
    '.png'  : 'image/png',
    '.jpg'  : 'image/jpeg',
    '.jpeg' : 'image/jpeg',
    '.gif'  : 'image/gif',
    '.svg'  : 'image/svg+xml',
    '.ico'  : 'image/x-icon',
    '.woff2': 'font/woff2',
    '.woff' : 'font/woff',
    '.ttf'  : 'font/ttf',
    '.wasm' : 'application/wasm',
    '.glb'  : 'model/gltf-binary',
    '.gltf' : 'model/gltf+json',
    '.bin'  : 'application/octet-stream',
};

const STREAM_THRESHOLD = 512 * 1024;

const server = http.createServer((req, res) => {
    const ts = new Date().toLocaleTimeString('ko-KR');
    console.log(`[${ts}] ${req.method} ${req.url}`);

    let urlPath = decodeURIComponent(req.url.split('?')[0]);
    if (urlPath === '/') urlPath = '/gas_circulation_viewer/index.html';

    const absPath = path.resolve(path.join(PUBLIC, urlPath));
    if (!absPath.startsWith(path.resolve(PUBLIC))) {
        res.writeHead(403, { 'Content-Type': 'text/plain' });
        res.end('403 Forbidden');
        return;
    }

    const ext         = path.extname(absPath).toLowerCase();
    const contentType = MIME[ext] || 'application/octet-stream';
    const headers = {
        'Content-Type'                : contentType,
        'Access-Control-Allow-Origin' : '*',
        'Cache-Control'               : 'no-store',
        'Connection'                  : 'keep-alive',
    };

    fs.stat(absPath, (err, stat) => {
        if (err) {
            if (err.code === 'ENOENT') {
                res.writeHead(404, { 'Content-Type': 'text/html; charset=utf-8' });
                res.end(`<h2>404 Not Found</h2><code>${urlPath}</code>`);
            } else {
                res.writeHead(500, { 'Content-Type': 'text/plain' });
                res.end('500 Internal Server Error');
            }
            console.error(`  ❌ ${err.code}: ${absPath}`);
            return;
        }

        headers['Content-Length'] = stat.size;

        if (stat.size >= STREAM_THRESHOLD) {
            res.writeHead(200, headers);
            const stream = fs.createReadStream(absPath);
            stream.on('error', (sErr) => {
                console.error(`  ❌ 스트림 오류: ${sErr.message}`);
                if (!res.headersSent) {
                    res.writeHead(500, { 'Content-Type': 'text/plain' });
                }
                res.end();
            });
            stream.pipe(res);
            console.log(`  ✅ 200 ${contentType} (${(stat.size / 1024 / 1024).toFixed(2)}MB, 스트리밍)`);
        } else {
            fs.readFile(absPath, (rErr, data) => {
                if (rErr) {
                    console.error(`  ❌ ${rErr.code}: ${absPath}`);
                    res.writeHead(500, { 'Content-Type': 'text/plain' });
                    res.end('500 Internal Server Error');
                    return;
                }
                res.writeHead(200, headers);
                res.end(data);
                console.log(`  ✅ 200 ${contentType} (${(data.length / 1024).toFixed(1)}KB)`);
            });
        }
    });
});

const connections = new Set();
server.on('connection', (socket) => {
    connections.add(socket);
    socket.on('close', () => connections.delete(socket));
});

server.listen(PORT, HOST, () => {
    let localIP = 'localhost';
    for (const ifaces of Object.values(os.networkInterfaces())) {
        for (const iface of ifaces) {
            if (iface.family === 'IPv4' && !iface.internal) {
                localIP = iface.address;
                break;
            }
        }
    }

    const memMB = (process.memoryUsage().rss / 1024 / 1024).toFixed(1);
    console.log('\n' + '='.repeat(55));
    console.log('🛠  Gas Circulation Process Modifier 3D Viewer');
    console.log('='.repeat(55));
    console.log(`📍 로컬    : http://localhost:${PORT}`);
    console.log(`📍 네트워크: http://${localIP}:${PORT}`);
    console.log(`📂 루트    : ${PUBLIC}`);
    console.log(`🧠 초기 메모리: ${memMB} MB`);
    console.log('='.repeat(55));
    console.log('종료: Ctrl + C\n');
});

server.on('error', (err) => {
    if (err.code === 'EADDRINUSE') {
        console.error(`❌ 포트 ${PORT} 이미 사용 중`);
        console.error('   다른 터미널에서 실행 중인 서버를 종료하거나');
        console.error('   server.js의 PORT 변수를 다른 번호로 변경하세요.\n');
    } else {
        console.error('서버 오류:', err.message);
    }
    process.exit(1);
});

let shuttingDown = false;
const FORCE_EXIT_MS = 5000;

function shutdown(signal) {
    if (shuttingDown) return;
    shuttingDown = true;

    const memMB = (process.memoryUsage().rss / 1024 / 1024).toFixed(1);
    console.log(`\n${signal} 수신 — 서버 종료 중... (현재 RSS ${memMB} MB)`);

    server.close(() => {
        console.log('✅ 모든 연결 정상 종료');
        process.exit(0);
    });

    if (typeof server.closeAllConnections === 'function') {
        server.closeAllConnections();
    } else {
        for (const socket of connections) socket.destroy();
    }

    const forceTimer = setTimeout(() => {
        console.warn(`⚠️  ${FORCE_EXIT_MS / 1000}초 내 종료되지 않음 — 강제 종료`);
        process.exit(0);
    }, FORCE_EXIT_MS);
    forceTimer.unref();
}

process.on('SIGINT',  () => shutdown('SIGINT (Ctrl+C)'));
process.on('SIGTERM', () => shutdown('SIGTERM'));

process.on('uncaughtException', (err) => {
    console.error('❌ 예상치 못한 오류:', err.message);
    shutdown('uncaughtException');
});