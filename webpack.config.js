module.exports = {
  entry: [
    './axibot/server/js/app.js',
    './axibot/server/css/app.scss'
  ],
  output: {
    filename: './axibot/server/dist/main.js'
  },
  resolve: {
    alias: {
      'vue$': 'vue/dist/vue.common.js'
    }
  },
  module: {
    rules: [
      {
        test: /\.css$/,
        use: ["style-loader", "css-loader"]
      },
      {
        test: /\.scss$/,
        use: ["style-loader", "css-loader", "sass-loader"]
      }
    ]
  }
}
