Join the [{{ city }} Sunday Night Film Club]({{ clubURL }}) this {{ nextSunday }}{{ daySuffix }} at {{ showTime }} for [{{ film }}]({{ filmURL }}) at the [{{ location }}]({{ locationURL }}). Look for [{{ host }}]({{ hostURL }}) wearing {{ wearing }} in the theatre lobby about 15 minutes before the film. As always, after the film we will descend on a local establishment for dinner/drinks/discussion.

{% for paragraph in synopsis %}
{{ paragraph }}
{% endfor %} 