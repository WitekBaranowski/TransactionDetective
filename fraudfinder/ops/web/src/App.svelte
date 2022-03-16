<script>
  import { Tabs, TabList, TabPanel, Tab } from "./tabs.js";
  import Config from "./Config.svelte";
  import Datagen from "./Datagen.svelte";
  import Predict from "./Predict.svelte";
  import Dashboard from "./Dashboard.svelte";
  //import Datasets from "./Datasets.svelte";
  import Models from "./Models.svelte";
  import Endpoints from "./Endpoints.svelte";

  let endpoint_id = "";
  let datagen_url = "";
  let predict_url = "";
  let dashboard_url = "";
  let server_url = "";
  let featurestore_id = "";
</script>

<main>
  <img class="center" alt="Fraud Finder" height="100" src="logo.png" />
  <br />
  <Tabs>
    <TabList>
      <Tab>Config</Tab>
      <Tab>Datagen</Tab>
      <Tab>Predict</Tab>
      <Tab>Dashboard</Tab>
      <!-- <Tab>Datasets</Tab> -->
      <Tab>Models</Tab>
      <Tab>Endpoints</Tab>
    </TabList>
    <TabPanel>
      <Config
        bind:endpoint_id
        bind:datagen_url
        bind:predict_url
        bind:dashboard_url
        bind:server_url
        bind:featurestore_id
      />
    </TabPanel>
    <TabPanel>
      {#key datagen_url}
        <Datagen url={datagen_url} />
      {/key}
    </TabPanel>
    <TabPanel>
      {#key predict_url}
        {#key endpoint_id}
          {#key featurestore_id}
            <Predict
              url={predict_url}
              eid={endpoint_id}
              fsid={featurestore_id}
            />
          {/key}
        {/key}
      {/key}
    </TabPanel>
    <TabPanel>
      {#key dashboard_url}
        <Dashboard url={dashboard_url} />
      {/key}
    </TabPanel>
    <!--
    <TabPanel>
      {#key server_url}
        <Datasets url={server_url} />
      {/key}
    </TabPanel>
    -->
    <TabPanel>
      {#key server_url}
        <Models url={server_url} />
      {/key}
    </TabPanel>
    <TabPanel>
      {#key server_url}
        <Endpoints url={server_url} />
      {/key}
    </TabPanel>
  </Tabs>
</main>

<style>
  :global(table) {
    border-collapse: collapse;
    margin-left: auto;
    margin-right: auto;
    font-size: 0.9em;
    font-family: sans-serif;
    min-width: 400px;
    box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
  }
  :global(table thead tr) {
    background-color: #76bb3f;
    color: #000000;
    text-align: center;
  }
  :global(table tbody tr) {
    border-bottom: 1px solid #dddddd;
  }
  :global(tr td) {
    padding: 6px 8px;
  }
  :global(tr:nth-of-type(even)) {
    background-color: #d8f3c1;
  }
  :global(tr:last-of-type) {
    border-bottom: 2px solid #d8f3c1;
  }
  :global(tr.active-row) {
    font-weight: bold;
    color: #009879;
  }
  :global(.loading) {
    opacity: 0;
    animation: 0.4s 0.8s forwards fade-in;
  }
  @keyframes fade-in {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }
  main {
    text-align: center;
    padding: 1em;
    max-width: 240px;
    margin: 0 auto;
  }
  .center {
    display: block;
    margin-left: auto;
    margin-right: auto;
  }
  h1 {
    /* color: #ff3e00; */
    text-align: center;
    text-transform: uppercase;
    font-size: 4em;
    font-weight: 100;
    display: flex;
    align-items: center;
  }
  @media (min-width: 640px) {
    main {
      max-width: none;
    }
  }
  :global(#table-wrapper) {
    position: relative;
  }
  :global(#table-scroll) {
    height: 450px;
    overflow: auto;
    margin-top: 10px;
  }
  :global(#table-wrapper table) {
    width: 90%;
  }
  :global(#table-wrapper table thead th .text) {
    position: absolute;
    top: -20px;
    z-index: 2;
    height: 20px;
    width: 35%;
    border: 1px solid red;
  }
  :global(th) {
    height: 30px;
    color: white;
    background-color: #006600;
    position: sticky;
    top: 0; /* Don't forget this, required for the stickiness */
  }
</style>
