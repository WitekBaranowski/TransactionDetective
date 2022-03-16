<script>
  import { onDestroy } from "svelte";
  onDestroy(() => socket.disconnect());
  export let url;
  if (url == "") {
    url = "https://datagen.fraudfinder.app";
  }
  import io from "socket.io-client";
  let socket = io(url, { transports: ["websocket"], reconnectionDelay: 2000 });
  let connected = false;
  let started_streaming = false;
  let state = { batch: "idle", stream: "idle" };
  function clicked(mode) {
    if (state[mode] === "running") {
      if (connected) {
        state[mode] = "idle";
        socket.emit("stop");
      }
    } else if (state["batch"] === "idle" && state["stream"] === "idle") {
      if (connected) {
        state[mode] = "running";
        if (started_streaming == true) {
          socket.emit("continue");
        } else {
          socket.emit(mode);
          started_streaming = true;
        }
      }
    }
  }

  socket.on("connect", function (msg) {
    connected = true;
  });

  socket.on("disconnect", function (msg) {
    connected = false;
  });

  socket.on("log", (msg) => {
    console.log(msg.data);
  });

  socket.on("tx", (msg) => {
    console.log(msg.data);
    let table = document.getElementById("stream_table");
    let row = table.insertRow(-1);
    let cells = [
      "TX_TS",
      "TERMINAL_ID",
      "TERMINAL_ID",
      "TX_AMOUNT",
      "CARDPRESENT_HACKED",
      "CARDNOTPRESENT_HACKED",
      "TERMINAL_HACKED",
      "TX_FRAUD",
    ];
    let front = "";
    let back = "";
    if (msg.data["TX_FRAUD"] != 0) {
      front = "<mark>";
      back = "</mark>";
    }
    for (let i = 0; i < cells.length; i++) {
      var cell = row.insertCell(i);
      cell.innerHTML = front + msg.data[cells[i]] + back;
    }
    var div = document.getElementById("table-scroll");
    div.scrollTop = div.scrollHeight;
  });
</script>

<br />
<div>
  Data Generator Status:
  <strong>{connected ? "Connected" : "Not Connected"}</strong> ({url})
</div>

<!--
<button
  class:selected={state["batch"] === "running"}
  on:click={() => clicked("batch")}
>
  {state["batch"] === "idle" ? "Start" : "Stop"} Batch</button
>
-->

<button
  class:selected={state["stream"] === "running"}
  on:click={() => clicked("stream")}
  >{state["stream"] === "idle" ? "Start" : "Stop"} Stream</button
>

<div id="table-wrapper">
  <div id="table-scroll">
    <table id="stream_table">
      <thead
        ><tr>
          <th>TX_TS</th>
          <th>CUSTOMER_ID</th>
          <th>TERMINAL_ID</th>
          <th>TX_AMOUNT</th>
          <th>CP_HACKED</th>
          <th>CNP_HACKED</th>
          <th>TERMINAL_HACKED</th>
          <th>TX_FRAUD</th>
        </tr></thead
      >
      <tbody />
    </table>
  </div>
</div>

<style>
  button {
    margin: 15px;
    background-color: #d8f3c1;
  }
  .selected {
    background-color: red;
  }
</style>
