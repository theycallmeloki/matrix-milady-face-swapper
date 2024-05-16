import { send } from 'micro';
import { compose } from 'micro-hoofs';

const cors = (handler) => async (req, res) => {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  res.setHeader(
    "Access-Control-Allow-Headers",
    "Origin, X-Requested-With, Content-Type, Accept"
  );

  if (req.method === "OPTIONS") {
    return res.status(200).end();
  }

  return handler(req, res);
};


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
