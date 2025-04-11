import {scrapeMaster} from "./scrape/scrapeWrapper.js"
import { readFile } from 'fs/promises';

let config_file = './.config.json'
if ( process.argv.length > 2) {
    config_file = process.argv[2]
}

let config = JSON.parse(await readFile(config_file, "utf8"));

scrapeMaster(config)