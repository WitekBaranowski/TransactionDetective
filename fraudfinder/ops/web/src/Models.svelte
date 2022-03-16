<script>
  export let url;
  if (url == "") {
    url = "https://server.fraudfinder.app";
  }
  import { onMount } from "svelte";
  import Model from "./Model.svelte";
  let models;
  let connected = true;

  onMount(async () => {
    await fetch(url + "/models")
      .then((r) => r.json())
      .then((data) => {
        models = data;
      });
  });
</script>

<br />
<div>
  Models Status:
  <strong>{connected ? "Connected" : "Not Connected"}</strong> ({url})
</div>
<br />

{#if models}
  <table>
    <thead>
      <tr>
        <th>Id</th>
        <th>Name</th>
        <th>Schema</th>
      </tr>
    </thead>
    <tbody>
      {#each models as model}
        <Model {model} />
      {/each}
    </tbody>
  </table>
{:else}
  <p class="loading">loading...</p>
{/if}

<style>
</style>
