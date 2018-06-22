//require("./node_modules/web3/dist/web3.min.js");
//require("./contract.js");

function init_web3(ip) {
    return web3 = new Web3(new Web3.providers.HttpProvider(ip));
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
        reader.addEventListener('load', function (e) {
           keystore.value = e.target.result;
           console.log(keystore.value);
        });
        reader.readAsBinaryString(key_file)
      }
    });
}
/* 
function deposit_sbtc(sbtc_amount, web3_eth, web3_rsk) {
    web3.eth.getAccounts(function(err, accounts) {console.info(accounts);});

        var stride_rsk = contract.at('0xc589638371dB9C7D00003a8E638A6b4910097996'); 
        console.log(stride_rsk);
          var sbtc = parseFloat(document.getElementById("sbtc").value); 
            sbtc_wei = web3.toWei(sbtc, "ether"); 
            var dest = document.getElementById("dest").value;
            console.info("calling deposit");
            document.getElementById("status").innerHTML = "Processing ..";
            var account = web3.eth.accounts[0];
            stride_rsk.depositSBTC(dest, {
                    from: account, 
                    gasPrice: "0.00000001", 
                    gas: 4000000, 
                    value: sbtc_wei
                }, function(error, result) {
                    if (error) {
                        console.error(error);
                        document.getElementById("status").innerHTML = "ERROR";
                        err = true;
                    }
                    else { 
                        txn_hash = result;
                        console.info(txn_hash);
                        wait_to_be_mined(txn_hash);
                    } 
                }
            );
        });
}

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

