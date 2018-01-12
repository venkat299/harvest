const Promise = require('bluebird');
const fs = require('fs');
const Mimicry = require('mimicry');
const moment = require('moment');
const parse = require('csv-parse');
const unzip = require('unzip');
const path = require('path');
const mimic_browser = new Mimicry();
const logger = require('./app_logger').logger;
// const request = Promise.promisifyAll(require('request'));
// =======================
// private lib
// =======================
const api_key = require('./js_api_config').quandl_api_key;

function calculate_prev_date(moment_date) {
  const time_now = moment_date.format('HH');
  const day_today = moment_date.format('ddd');
  let date_needed = moment_date;

  logger.debug('downloading eod > current hr:', time_now, ' current day:', day_today);

  if (day_today.toUpperCase() === 'SUN') date_needed = date_needed.subtract(2, 'days');
  else if (day_today.toUpperCase() === 'SAT') date_needed = date_needed.subtract(1, 'days');
  else if ((+time_now) < 17) {
    if (day_today.toUpperCase() === 'MON') date_needed = date_needed.subtract(3, 'days');
    else date_needed = date_needed.subtract(1, 'days');
  }

  return date_needed;
}

function nse_eod(options) {
  const seneca = this;
  // the logging function, built by init
  const app_config =  {"data_provider":{
    current_dp_eod:"nse",
    "quandl":{
      "url": "https://www.quandl.com/api/v3/datasets/NSE/@tradingsymbol.@format?api_key=@api_key",
      "api_key":api_key
    },
    "nse":{
      "url":"https://www.nseindia.com/content/historical/EQUITIES/@YYYY/@MMM/cm@DD@MMM@YYYYbhav.csv.zip",
      "filename":"cm@DD@MMM@YYYYbhav.csv"
    }
  }};
  const curr_db = {"json": {
      "db_type": "jsonfile-store",
      "db_config": {
        "folder": "./test/test_db"
      }
    }};
  // place all the patterns together
  // this make it easier to see them at a glance
  //this.add('role:data,comp:eod,cmd:download', download);
  //= ============= downloads eod data from quandl ======
  function download(opt, cb) {
    // logger.debug('in download', options)
    const final_cb = cb;
   // const symbol_list = opt.data;
    const task_list = [];
    const dp_name = app_config.data_provider.current_dp_eod;
    const dp = app_config.data_provider;
    let url = dp[dp_name].url;
    let fileName = dp[dp_name].filename;

    const date_needed = calculate_prev_date(moment());

    const yyyy = date_needed.format('YYYY');
    const mmm = date_needed.format('MMM').toUpperCase();
    const dd = date_needed.format('DD');
    url = url.replace(/@YYYY/g, yyyy).replace(/@MMM/g, mmm).replace(/@DD/g, dd);
    fileName = fileName.replace(/@YYYY/g, yyyy).replace(/@MMM/g, mmm).replace(/@DD/g, dd);
    logger.debug('downloading eod > url:', url);

    const save_path_zip = 'harvest/data/eod_nse/eod_' + yyyy + '_' + mmm + '_' + dd + '.csv.zip';
    const save_path_csv = 'harvest/data/eod_nse/eod_' + yyyy + '_' + mmm + '_' + dd + '.csv';
    const save_path_csv_latest = 'harvest/data/eod_nse/eod_latest.csv';
    fs.stat(save_path_csv, function (err, stats) {
      // download from NSE
      if (err || !stats.isFile()) download_csv({
        url,
        save_path_zip,
        save_path_csv,
        save_path_csv_latest,
        fileName,
      }, function (e) {
        if (e) final_cb(e);
        else
        {
          // save_to_db(save_path_csv, final_cb);
           logger.debug('download complete')
        }
       
      });
      else {
        logger.debug('skipping eod file download as file is already present');
        //save_to_db(save_path_csv, final_cb);
      }
    });
  }

  function download_csv(opt, cb) {
    try {
      mimic_browser.get(opt.url, function (err, data) {
        if(err) cb(err);
        fs.writeFile(opt.save_path_zip, data, function (err, written, buffer) {
          if(err) cb(err);
          logger.debug('in write file');
          fs.createReadStream(opt.save_path_zip).pipe(unzip.Parse()).on('entry', function (entry) {
            const fileName = entry.path;
            const type = entry.type; // 'Directory' or 'File'
            const size = entry.size;
            if (fileName === opt.fileName) {
              entry.pipe(fs.createWriteStream(opt.save_path_csv_latest));
              entry.pipe(fs.createWriteStream(opt.save_path_csv)); 
            } else {
              entry.autodrain();
            }
          }).on('close', function () {
            cb();
          }).on('error',function(err){
            logger.error('ERR:PROBLEM_IN_DOWNLOADING_RESOURCE',err);
            cb(err);
          });
        });
      });
    } catch (e) {
      cb(e);
    }
  }
  //= ============= converts downloaded message to consumable format ======
  function transform_eod(raw) {
    // note: quandl specific conversion
    const columns = ['date', 'open', 'high', 'low', 'last', 'close', 'volume', 'turnover'];
    const data = raw.dataset.data[0].reduce(function (result, field, index) {
      result[columns[index]] = field;
      return result;
    }, {});
    // add extra fields
    data.timestamp = (new Date(data.date)).toISOString();
    data.tradingsymbol = raw.dataset.dataset_code;
    // note: kite specific conversion
    // var columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume'];
    // var data = mock_dt.data.candles[0].reduce(function(result, field, index) {
    //  result[columns[index]] = field;
    //  return result;
    // }, {});
    return data;
  }
  //= ============= saves eod data to db
  function save_to_db(path, cb) {
    if (curr_db === 'json') {
      const db_path = app_config.test[curr_db].db_config.folder;
      rmDir(db_path + '/eod', false);
    }
    // var eod = seneca.make$('eod')
    // var eod_list$ = Promise.promisify(eod.list$, {
    //     context: eod
    // })
    // eod_list$().then(function(ls) {
    //     ls.forEach(function(ls_item) {
    //         ls_item.remove$()
    //     })
    logger.debug('path:', path);
    const task_arr = [];
    const parser = parse({
      columns: true,
    }, function (err, data) {
      logger.debug('data.length:', data.length);
      data.forEach(function (item) {
        const ent = {
          tradingsymbol: item.SYMBOL,
          SERIES: item.SERIES,
          open: parseFloat(item.OPEN),
          high: parseFloat(item.HIGH),
          low: parseFloat(item.LOW),
          close: parseFloat(item.CLOSE),
          last: parseFloat(item.LAST),
          prevclose: parseFloat(item.PREVCLOSE),
          qty: parseInt(item.TOTTRDQTY),
          volume: parseInt(item.TOTTRDVAL),
          timestamp: item.TIMESTAMP,
          trades: parseInt(item.TOTALTRADES),
          ISIN: item.ISIN,
        };
        task_arr.push(new Promise(function (res, rej) {
          seneca.make$('eod', ent).save$(function (err) {
            if (err) rej();
            res();
          });
        }));
      });
      Promise.all(task_arr).then(function () {
        cb(null, {
          success: true,
        });
      }).catch(e => {
        cb(e);
      });
    });
    fs.createReadStream(path).pipe(parser);
    // })
  }

  function after_save(err, val) {
    if (err) logger.debug(err);
    logger.debug('eod data saved:', val.tradingsymbol);
  }

  function rmDir(dirPath, removeSelf) {
    if (removeSelf === undefined) removeSelf = true;
    try {
      var files = fs.readdirSync(dirPath);
    } catch (e) {
      // throw e
      return;
    }
    if (files.length > 0)
      for (let i = 0; i < files.length; i++) {
        const filePath = path.join(dirPath, files[i]);
        if (fs.statSync(filePath).isFile()) fs.unlinkSync(filePath);
        else rmDir(filePath);
      }
    if (removeSelf) fs.rmdirSync(dirPath);
  }

  download({},console.log);
}
module.exports = nse_eod;

(function(){
  nse_eod();
})()
