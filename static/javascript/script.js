const orderitemslist = []
function addItem(itemID) {
    console.log(itemID)
    orderitemslist.push(itemID)
    console.log(orderitemslist)
    return orderitemslist;
}  

function sendlist() {
    console.log(orderitemslist)
    const request = new XMLHttpRequest()
    request.open("POST", `/cart/${(orderitemslist)}`)
    request.send()
}

function sendCheckout() {
    const insertRequest = new XMLHttpRequest()
    insertRequest.open("POST", `/system/insert`)
    insertRequest.send()
    setTimeout(function(){window.open("/retail/options", '_self')}, 500);
}

function reorder(OrderID) {
    const reorderRequest = new XMLHttpRequest()
    console.log(OrderID)
    reorderRequest.open("POST", `/system/${(OrderID)}`)
    reorderRequest.send()
    setTimeout(function(){window.open("/retail/options", '_self')}, 500);
}

function delay(URL) {
    setTimeout( function() { window.location = URL }, 500 );
}