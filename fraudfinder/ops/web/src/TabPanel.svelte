<script>
  import { getContext } from "svelte";
  import { TABS } from "./Tabs.svelte";

  const panel = {};
  const { registerPanel, selectedPanel } = getContext(TABS);

  registerPanel(panel);
</script>

<div hidden={$selectedPanel !== panel}>
    <slot></slot>
</div>

<!--
{#if $selectedPanel === panel}
  <slot />
{/if}
-->
