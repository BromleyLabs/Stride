
function init_web3(ip) {
    return web3 = new Web3(new Web3.providers.HttpProvider(ip));
}

function get_pvt_key(key_contents, password) {
    keyobj = JSON.parse(key_contents); 
    from_addr = "0x" + keyobj.address
    from_addr = web3.toChecksumAddress(from_addr);
    return [keythereum.recover(password, keyobj), from_addr];
}

// input_id is element id for file input
// keystore_id is an hidden div where key contents are stored
function get_account_key(input_id, keystore_id) {
    var input = document.getElementById(input_id);
    var keystore = document.getElementById(keystore_id);
    input.addEventListener("change", function () {
        if (this.files && this.files[0]) {
            var key_file = this.files[0];
            var reader = new FileReader();
            reader.readAsText(key_file);
            reader.addEventListener('load', function (e) {
                keystore.value = e.target.result;
                //console.log(keystore.value);
            });
        }
    });
}

function deposit_sbtc(key_contents, password, sbtc_amount, dest_addr, 
                      contract_rsk, contract_eth, web3_eth, web3_rsk) {
    sbtc_wei = web3.toHex(web3.toWei(sbtc_amount, "ether")); 
    [pvt_key, from_addr] = get_pvt_key(key_contents, password);
    console.info("from addr:" + from_addr);
    web3_rsk.eth.getTransactionCount(from_addr, function(err, nonce) {
        console.info(nonce);
        var data = contract_rsk.depositSBTC.getData(dest_addr);  
        var tx = new ethereumjs.Tx({
            nonce: nonce,           
            gasPrice: web3.toHex(web3.toWei('0', 'gwei')), 
            gasLimit: 4000000, 
            to: contract_rsk.address,
            value: sbtc_wei,
            data: data,
        });

        console.info("Signing ..");
        tx.sign(pvt_key);
        var raw = '0x' + tx.serialize().toString('hex');
        console.info(raw);
        console.info("Calling send raw txn..");
        web3_rsk.eth.sendRawTransaction(raw, function(err, txn_hash) {
            if (err) 
                console.error("Error sending Txn");
            else
                console.log(txn_hash); 
        });
    });
}

/* 
function wait_to_be_mined(txhash) {
    console.info("Getting txn receipt");
    web3.eth.getTransactionReceipt(txhash, function (err, result) {
        if (!err && !result) {
            // Try again with a bit of delay
            setTimeout(function () {wait_to_be_mined (txhash) }, 2000);
            console.info("Trying to get receipt again");
        } else {
            if (err)
                console.error("ERROR in Transaction"); 
            else
                console.info("Transaction mined"); 
        }
    });
}

*/


