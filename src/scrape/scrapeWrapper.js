import { CompanyTypes, createScraper } from 'israeli-bank-scrapers';
import { parse as objToCsv } from 'json2csv'
import fs from 'fs';


async function scrapeJob(credentials, options) {
  const scraperName = credentials.companyId + '_' + credentials.username ;
  console.log(`Working on - ${scraperName}`) ;
  try {
    options.companyId = credentials.companyId;
    if ("startDate" in options ) { 
      options.startDate = new Date(options.startDate);
    } else {
      // if no startDate in config file get extract data of current month
      let date = new Date(); 
      options.startDate = new Date(date.getFullYear(), date.getMonth(), 0);
    }

    const scraper = createScraper(options)
    const scrapeResult = await scraper.scrape(credentials);
    if (scrapeResult.success) {
      scrapeResult.accounts.forEach((account) => {
        let data = account.txns
        // Remove installment field from every transactions
        //data.forEach((obj) => {
        //  for (const key in obj) {
        //    if (obj[key] == "") {
        //      obj[key] = "None"
        //    }
        //  }
        //  obj["installments"] = undefined ;
        //}); 
        const fields = ["identifier","date","chargedAmount","originalCurrency","type","category","description","status"]
        let csv = objToCsv(data, { fields });
        const suffix = scraperName + '_' + account.accountNumber
        const filename = './data/transactions_' + suffix + '.csv'
        if (fs.existsSync(filename)) {
          //remove title
          csv = csv.split('\n');
          csv.shift();
          csv = "\n" + csv.join('\n');
          console.log(csv)
          fs.appendFile(filename, csv, (err) => { if (err) { console.error(err); return;}});
        } else {
          fs.writeFile(filename, csv, (err) => { if (err) { console.error(err); return;}});
        }
        console.log(`${scraperName} - found ${account.txns.length} transactions for account number ${account.accountNumber}`);
      });
    } else {
      throw new Error(scrapeResult.errorType);
    }
  } catch(e) {
     console.error(`${scraperName} - scraping failed for the following reason: ${e.message}`);
  }
};

export async function scrapeMaster(config) {
    console.log("options:\n", config.options);

    for (const idx in config.credentials) {
        const scraper = config.credentials[idx]
        scrapeJob(scraper, config.options)
    }
}
