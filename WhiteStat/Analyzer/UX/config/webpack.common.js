const paths = require('./paths');
const webpack = require('webpack');

module.exports = {
  entry: {
    main: paths.appEntry
  },
  output: {
    publicPath: '/'
  },
  externals: {
    chartjs: 'Chart',
    jquery: 'jQuery',
    'perfect-scrollbar': 'PerfectScrollbar'
  },
  resolve: {
    alias: {
        'jquery': paths.nodemods + '/jquery/dist/jquery.min.js'
    }
},
plugins: [ new webpack.ProvidePlugin({
  $: 'jquery',
  jQuery: 'jquery',
  'window.jQuery': 'jquery'
}) ],
  module: {
    rules: [
      {
        test: /\.txt/,
        loader: 'file-loader',
        options: {
          interpolate: true
        }
      },
      {
        test: /\.html/,
        loader: 'html-loader',
        options: {
          interpolate: true
        }
      },
      {
        test: /\.hbs$/,
        use: [
          {
            loader: 'handlebars-loader',
            options: {
              helperDirs: paths.handlebarsHelpers
            }
          },
          {
            loader: 'extract-loader'
          },
          {
            loader: 'html-loader',
            options: {
              interpolate: true
            }
          }
        ]
      },
      {
        test: /\.(svg|png|jpg|jpeg|gif)$/,
        use: {
          loader: 'file-loader',
          options: {
            name: '[name].[ext]',
            outputPath: 'images'
          }
        }
      },
      {
        test: /\.(js|mjs)$/,
        exclude: /node_modules/,
        use: ['babel-loader', 'eslint-loader']
      }
    ]
  }
};
