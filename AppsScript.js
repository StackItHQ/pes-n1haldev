function onEdit() {
    var sheet = SpreadsheetApp.getActiveSpreadsheet();
    var sheetId = sheet.getId();
    var sheetName = sheet.getActiveSheet().getName();
    var data = sheet.getActiveSheet().getDataRange().getValues();
  
    var options = {
      'method': 'post',
      'contentType': 'application/json',
      'payload': JSON.stringify(data)
    };
  
    var url = "https://d74f-2406-7400-94-b3af-c04e-c649-5881-c9da.ngrok-free.app/api/init";
    
    try {
      UrlFetchApp.fetch(url, options);
      Logger.log("Data sent to ngrok server successfully.");
    } catch (error) {
      Logger.log("Error sending data to ngrok server: " + error.message);
    }
  }