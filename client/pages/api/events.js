import { send } from 'micro';
import { compose } from 'micro-hoofs';

import cors from '../utils/cors';

const eventHandler = (req, res) => {
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');
    res.flushHeaders();

    const intervalId = setInterval(() => {
        res.write(`data: ${JSON.stringify({ timestamp: Date.now() })}\n\n`);
    }, 1000);

    req.on('close', () => {
        clearInterval(intervalId);
    });
};

const handler = compose(cors)(eventHandler);

export default handler;
