<script>
  export let url;
  if (url == "") {
    url = "https://server.fraudfinder.app";
  }
  import { onMount } from "svelte";
  import Endpoint from "./Endpoint.svelte";
  let endpoints;
  let connected = true;

  onMount(async () => {
    await fetch(url + "/endpoints")
      .then((r) => r.json())
      .then((data) => {
        endpoints = data;
      });
  });
</script>

<br />
<div>
  Endpoints Status:
  <strong>{connected ? "Connected" : "Not Connected"}</strong> ({url})
</div>
<br />

{#if endpoints}
  <table>
    <thead>
      <tr>
        <th>Id</th>
        <th>Name</th>
        <th>Schema</th>
      </tr>
    </thead>
    <tbody>
      {#each endpoints as endpoint}
        <Endpoint {endpoint} />
      {/each}
    </tbody>
  </table>
{:else}
  <p class="loading">loading...</p>
{/if}

<style>
</style>
