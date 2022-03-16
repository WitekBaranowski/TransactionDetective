<script context="module">
  import { data } from "./stores.js";
  export const func = {
    get: function get() {
      return data;
    },
    add: function add(row) {
      data.push(row);
    },
  };
</script>
