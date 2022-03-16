<script>
  import { onDestroy } from "svelte";
  import { func } from "./Data.svelte";
  onDestroy(() => socket.disconnect());
  export let threshold = .5;
  export let url;
  if (url == "") {
    url = "https://predict.fraudfinder.app";
  }
  export let eid;
  if (eid == "") {
    eid = "5996727621797281792";
  }
  export let fsid;
  if (fsid == "") {
    fsid = "fraud_finder_845";
  }
  import io from "socket.io-client";
  let socket = io(url, { transports: ["websocket"], reconnectionDelay: 2000 });
  let connected = false;
  let state = { batch: "idle", stream: "idle" };

  socket.on("connect", function (msg) {
    connected = true;
    // Auto-start prediction stream.
    socket.emit("start");
    socket.emit("config", { endpoint_id: eid, featurestore_id: fsid });
  });

  socket.on("disconnect", function (msg) {
    connected = false;
  });

  socket.on("log", (msg) => {
    console.log(msg.data);
  });

  socket.on("tx", (msg) => {
    console.log(msg.data);
    let table = document.getElementById("predict_table");
    let row = table.insertRow(-1);
    let cells = [
      "prediction",
      "latency",
      "customer_id",
      "terminal_id",
      "tx_amount",
      "customer_id_nb_tx_1day_window",
      "customer_id_nb_tx_7day_window",
      "customer_id_nb_tx_14day_window",
      "customer_id_avg_amount_1day_window",
      "customer_id_avg_amount_7day_window",
      "customer_id_avg_amount_14day_window",
      "terminal_id_nb_tx_1day_window",
      "terminal_id_nb_tx_7day_window",
      "terminal_id_nb_tx_14day_window",
      "terminal_id_risk_1day_window",
      "terminal_id_risk_7day_window",
      "terminal_id_risk_14day_window",
    ];
    let front = "";
    let back = "";
    msg.data["fraud"] = "legitimate";
    if (msg.data["prediction"] > threshold) {
      msg.data["fraud"] = "fraudulent";
      front = "<mark>";
      back = "</mark>";
    }
    console.log("prediction:", msg.data);
    func.add(msg.data);
    for (let i = 0; i < cells.length; i++) {
      var cell = row.insertCell(i);
      var key = cells[i];
      var val = msg.data[key];
      if (
        val &&
        (key == "prediction" ||
          key == "latency" ||
          key.includes("risk") ||
          key.includes("avg"))
      ) {
        val = val.toFixed(4);
      }
      cell.innerHTML = front + val + back;
    }
    var div = document.getElementById("table-scroll");
    div.scrollTop = div.scrollHeight;
  });

  /*
  let d = [
    { letter: "A", frequency: 0.00217 },
    { letter: "B", frequency: 0.00074 },
    { letter: "C", frequency: 0.03333 },
  ];
  let i = 0;
  function foo() {
    func.add(d[i]);
    i++;
  }
  */
</script>

<br />

<div>
  Predictor Status:
  <strong>{connected ? "Connected" : "Not Connected"}</strong> ({url}) Endpoint: {eid}
  Feature Store: {fsid}
</div>
<br />

<strong>Fraud Probability Threshold</strong>&nbsp;&nbsp;<input size="4" bind:value={threshold}>

<br />

<div id="table-wrapper">
  <div id="table-scroll">
    <table id="predict_table">
      <thead>
        <tr>
          <th>PREDICTION</th>
          <th>LATENCY</th>
          <th>C_ID</th>
          <th>T_ID</th>
          <th>TX_AMOUNT</th>
          <th>C_NUM_1</th>
          <th>C_NUM_7</th>
          <th>C_NUM_14</th>
          <th>C_AVG_1</th>
          <th>C_AVG_7</th>
          <th>C_AVG_14</th>
          <th>T_NUM_1</th>
          <th>T_NUM_7</th>
          <th>T_NUM_14</th>
          <th>T_RISK_1</th>
          <th>T_RISK_7</th>
          <th>T_RISK_14</th>
        </tr>
      </thead>
      <tbody />
    </table>
  </div>
</div>

<style>
  button {
    margin: 50px;
    background-color: #d8f3c1;
  }
  .selected {
    background-color: red;
  }
</style>
