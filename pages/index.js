const puppeteer = require('puppeteer');
const hbs = require('handlebars');
const fs = require('fs-extra');
const path = require('path');
const sessionData = require('./list.json'); // Load the session data
const listFilePath = path.join(process.cwd(), 'list.json'); // Path to the list.json file

// Function to compile hbs to pdf
const compile = async function (templateName, data) {
    const filePath = path.join(process.cwd(), 'Template', `${templateName}`);
    const html = await fs.readFile(filePath, 'utf-8');
    return hbs.compile(html)(data);
};

(async function() {
    try {
        const browser = await puppeteer.launch({ headless: "new" });
        const page = await browser.newPage();
        
        // Initialize an empty object for storing the list data
        let listData = {};

        // Check if list.json file exists, and load its content if it does
        if (fs.existsSync(listFilePath)) {
            listData = await fs.readJson(listFilePath);
        }

        // Iterate through session data
        for (const sessionItem of sessionData) {
            // Check if the session item has a json_file_path
            if (sessionItem.json_file_path) { // Update to match your session data structure
                const jsonFilePath = path.join(process.cwd(), sessionItem.json_file_path);

                // Read JSON data from the specified JSON file
                const jsonData = await fs.readJson(jsonFilePath);
                
                // Set the output file name based on the JSON file name
                const pdfName = path.join(process.cwd(), 'data/pdf_data', path.basename(sessionItem.json_file_path, '.json') + '.pdf'); // Modify the path here

                // Compile the PDF content using the JSON data
                const content = await compile('index.hbs', jsonData);
                
                await page.setContent(content);
                await page.waitForSelector('.banner-image'); // Replace '.banner-image' with your actual image selector
                
                // Creating a pdf doc with the specified output file name
                await page.pdf({
                    path: pdfName,
                    format: 'A4',
                    printBackground: true,
                });

                console.log(`Done creating PDF: ${pdfName}`);
                
                // Update the listData object with the new entry, using the 'name' as the key
                listData[sessionItem.name] = pdfName;
            } else {
                console.log(`JSON file path not found for session item: ${JSON.stringify(sessionItem)}`);
            }
        }

        // Write the updated listData to list.json
        await fs.writeJson(listFilePath, listData, { spaces: 4 });

        await browser.close();
        process.exit();
    } catch (e) {
        console.log(e);
    }
})();
