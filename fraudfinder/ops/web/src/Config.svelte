<script>
  import { onMount } from "svelte";
  export let endpoint_id;
  export let datagen_url;
  export let predict_url;
  //export let dashboard_url = localStorage.getItem("dashboard_url");
  export let server_url;
  export let featurestore_id;
  onMount(async () => {
    endpoint_id = localStorage.getItem("endpoint_id") || "";
    datagen_url = localStorage.getItem("datagen_url") || "";
    predict_url = localStorage.getItem("predict_url") || "";
    //dashboard_url = localStorage.getItem("dashboard_url") || "";
    server_url = localStorage.getItem("server_url") || "";
    featurestore_id = localStorage.getItem("featurestore_id") || "";
  });
</script>

<br /><br />
<table id="config-table">
  <tr>
    <td>
      <strong>Datagen URL: </strong>
    </td>
    <td>
      <input
        size="40"
        bind:value={datagen_url}
        on:input={() => localStorage.setItem("datagen_url", datagen_url)}
        placeholder="Enter datagen URL"
      />
    </td>
  </tr>
  <tr>
    <td>
      <strong>Predict URL: </strong>
    </td>
    <td>
      <input
        size="40"
        bind:value={predict_url}
        on:input={() => localStorage.setItem("predict_url", predict_url)}
        placeholder="Enter predict URL"
      />
    </td>
  </tr>
  <tr>
    <td>
      <strong>Server URL: </strong>
    </td>
    <td>
      <input
        size="40"
        bind:value={server_url}
        on:input={() => localStorage.setItem("server_url", server_url)}
        placeholder="Enter server URL"
      />
    </td>
  </tr>
  <tr>
    <td>
      <strong>Feature Store ID: </strong>
    </td>
    <td>
      <input
        size="40"
        bind:value={featurestore_id}
        on:input={() =>
          localStorage.setItem("featurestore_id", featurestore_id)}
        placeholder="Enter Feature Store ID"
      />
    </td>
  </tr>
  <tr>
    <td>
      <strong>Endpoint ID: </strong>
    </td>
    <td>
      <input
        size="40"
        bind:value={endpoint_id}
        on:input={() => localStorage.setItem("endpoint_id", endpoint_id)}
        placeholder="Enter Endpoint ID"
      />
    </td>
  </tr>
  <!--
  <tr>
    <td>
      <strong>Dashboard URL: </strong>
    </td>
    <td>
      <input
        size="40"
        bind:value={dashboard_url}
        on:input={() => localStorage.setItem("endpoint_id", endpoint_id)}
        placeholder="Enter dashboard URL"
      />
    </td>
  </tr>
-->
</table>

<style>
  table tr {
    background-color: initial;
  }
</style>
