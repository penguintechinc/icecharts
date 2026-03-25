#!/usr/bin/env node
/**
 * Action container server for Node.js runtime (OpenWhisk /init and /run pattern).
 */

const express = require('express');
const bodyParser = require('body-parser');
const fs = require('fs');

const app = express();
app.use(bodyParser.json());

let actionFunction = null;

app.post('/init', (req, res) => {
  const { code, handler } = req.body;

  // Write code to file
  fs.writeFileSync('/tmp/action.js', code);

  // Load module and handler
  try {
    const module = require('/tmp/action.js');
    const [moduleName, funcName] = handler.split('.');
    actionFunction = module[funcName];
    res.json({ status: 'ready' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/run', async (req, res) => {
  if (!actionFunction) {
    return res.status(400).json({ error: 'Action not initialized' });
  }

  try {
    const result = await actionFunction(req.body);
    res.json({ result });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.listen(8080, '0.0.0.0', () => {
  console.log('Action server listening on port 8080');
});
