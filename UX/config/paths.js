const { resolvePath } = require('./helpers');

module.exports = {
  src: resolvePath('src'),
  dist: resolvePath('dist'),
  nodemods: resolvePath('node_modules'),
  appEntry: resolvePath('src/index.js'),
  handlebarsHelpers: resolvePath('src/views/helpers')
};
