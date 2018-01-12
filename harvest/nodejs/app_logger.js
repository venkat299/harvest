const winston = require('winston');


const console_config = {
  level: 'debug',
  name: 'pretty_console',
  // handleExceptions: true,
  json: false,
  colorize: true,
  timestamp: true,
};

winston.remove(winston.transports.Console);
winston.add(winston.transports.Console, console_config);

// set log_level here
winston.level = 'debug';

// logger.exitOnError = false;

module.exports.logger = winston;