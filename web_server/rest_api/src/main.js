// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
import Vue from 'vue'
import App from './App'
import router from './router'
import axios from 'axios'
// This rows need to be included so that webpack renders it
// import 'materialize-css/dist/js/materialize.min.js'
// import 'materialize-css/dist/css/materialize.min.css'

Vue.config.productionTip = false

/* eslint-disable no-new */
new Vue({
  el: '#app',
  router,
  components: { App },
  template: '<App/>'
})

new Vue({
  el: '#app2',
  data: {
    rec_bands: '',
    user_id: '',
    loading: false
  },
  delimiters: ['[[', ']]'],
  methods: {
    get_rec_bands: function () {
      var user = {user_id: this.user_id}
      this.loading = true
      axios.post('http://localhost:8000/get_rec_bands/', user).then(response => {
        this.rec_bands = response.data
        this.loading = false
      })
    }

  }
})
