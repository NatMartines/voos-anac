{% materialization test, default %}
  {{ return(elementary.materialization_test_default()) }}
{% endmaterialization %}

{% materialization test, adapter="snowflake" %}
  {{ return(elementary.materialization_test_snowflake()) }}
{% endmaterialization %}