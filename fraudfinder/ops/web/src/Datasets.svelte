<script>
  export let url;
  if (url == "") {
    url = "https://server.fraudfinder.app";
  }
  import { onMount } from "svelte";
  import Dataset from "./Dataset.svelte";
  let datasets;
  let connected = true;

  onMount(async () => {
    await fetch(url + "/datasets")
      .then((r) => r.json())
      .then((data) => {
        datasets = data;
      });
  });
</script>

<br />
<div>
  Datasets Status:
  <strong>{connected ? "Connected" : "Not Connected"}</strong> ({url})
</div>
<br />

{#if datasets}
  <table>
    <thead>
      <tr>
        <th>Id</th>
        <th>Name</th>
        <th>Schema</th>
      </tr>
    </thead>
    <tbody>
      {#each datasets as dataset}
        <Dataset {dataset} />
      {/each}
    </tbody>
  </table>
{:else}
  <p class="loading">loading...</p>
{/if}

<style>
</style>
