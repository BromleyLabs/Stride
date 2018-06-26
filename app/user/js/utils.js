
function init_web3(ip) {
    return web3 = new Web3(new Web3.providers.HttpProvider(ip));
}

function get_pvt_key(key_contents, password) {
    keyobj = JSON.parse(key_contents); 
    from_addr = "0x" + keyobj.address
    from_addr = web3.toChecksumAddress(from_addr);
    return [keythereum.recover(password, keyobj), from_addr];
}

/* input_id is element id for file input
   keystore_id is a hidden div where key contents are stored
*/
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
            });
        }
    });
}

function deposit_sbtc(key_contents, password, sbtc_amount, dest_addr, 
                      contract_rsk, web3_rsk) {
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
        txn_hash = web3_rsk.eth.sendRawTransaction(raw);
        if (txn_hash == null) { 
            console.error("Error sending Txn");
            return;
        }
        console.log(txn_hash); 
        wait_to_be_mined(web3_rsk, txn_hash);
   });
}

function wait_to_be_mined(w3, txn_hash) {
    console.info("Getting txn receipt");
    w3.eth.getTransactionReceipt(txn_hash, function (err, result) {
        if (!err && !result) {
            // Try again with a bit of delay
            setTimeout(function () {wait_to_be_mined(w3, txn_hash) }, 3000);
        } else {
            if (err)
                console.error("ERROR in Transaction"); 
            else
                console.info("Transaction mined"); 
                start_block = w3.eth.blockNumber;
                wait_for_confirmations(w3, start_block, 2);   
        }
    });
}

function wait_for_confirmations(w3, start_block, n) {
    console.info("Waiting for enough confirmations");
    curr_block = w3.eth.blockNumber; 
    if ((curr_block - start_block) <= n) {
        setTimeout(function () {wait_for_confirmations(w3, start_block, n) }, 3000);
    }
    else {
        console.info(n + " confirmations done");
    }
}
