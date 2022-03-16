<script>
  import { onMount } from "svelte";
  import { func } from "./Data.svelte";
  import * as Plot from "@observablehq/plot";
  export let url;
  if (url == "") {
    url = "https://dashboard.fraudfinder.app";
  }
  let connected = false;

  onMount(async () => {
    setInterval(redraw, 1000);
  });
  let first1 = true;
  let first2 = true;
  let first3 = true;
  export function redraw() {
    let data = func.get();
    let options1 = {
      y: {
        grid: true,
      },
      marks: [
        Plot.areaY(
          data,
          Plot.binX({ y: "count" }, { x: "latency", fill: "#d8f3c1" })
        ),
        Plot.lineY(data, Plot.binX({ y: "count" }, { x: "latency" })),
        Plot.ruleY([0]),
      ],
    };
    let elem = document.getElementById("fig");
    if (first1) {
      elem.appendChild(Plot.plot(options1));
      first1 = false;
    } else {
      elem.replaceChild(Plot.plot(options1), elem.childNodes[0]);
    }

    let options2 = {
      x: {
        round: true,
        label: "Transaction Fraud",
      },
      y: {
        grid: true,
      },
      marks: [
        Plot.barY(
          data,
          Plot.groupX({ y: "count" }, { x: "fraud", fill: "#76bb3f" })
        ),
      ],
    };
    if (first2) {
      elem.appendChild(Plot.plot(options2));
      first2 = false;
    } else {
      elem.replaceChild(Plot.plot(options2), elem.childNodes[1]);
    }

    /*
    let options3 = {
      y: {
        grid: true,
      },
      marks: [
        Plot.areaY(
          data,
          Plot.binX({ y: "count" }, { x: "prediction", fill: "blue" })
        ),
        Plot.lineY(data, Plot.binX({ y: "count" }, { x: "prediction" })),
        Plot.ruleY([0]),
      ],
    };
    if (first3) {
      elem.appendChild(Plot.plot(options3));
      first3 = false;
    } else {
      elem.replaceChild(Plot.plot(options3), elem.childNodes[2]);
    }
    */
  }
</script>

<br />
<figure id="fig" />
