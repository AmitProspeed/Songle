//THIS FILE WILL:
//  - handle button clicks
//  - display data recieved from client.py (I hope)
//  EX:
//    - user clicks "make search" button
//    - search critera gets sent to client.py
//    - client.py sends search criteria to server (through a get request I think?)
//    - server sends results back to client.py
//    - client.py creats graphs and other things to display (because numpy is python library)
//    - client.py sends back results + graphs to homepage.js
//    - homepage.js displays the stuff
//    - (I have no idea if this will work how I want it to)


function sendQueryRequest(toSearch) {

        //TODO
  //Make a request to the server asking for a query
  //I think it would be a GET request?
}

function makeSearch() {
  let toSearch = document.getElementById('searchbar').value
  //TODO
  //CONDITIONAL TO FIND WHICH TOPIC OF DATA TO QUERY (ARTIST, ALBUM, SONGTITLE, LYRICS)
  //QUERY DATABASE TO FIND MATCHES
  //RETURN IN JSON FORMAT
  let resultsFromQuery = sendQueryRequest(toSearch.toLowerCase())
  displayData(queryResults)
}

