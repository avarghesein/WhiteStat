import Navigation from './Navigation';
import ScrollableComponents from './ScrollableComponents';
import Charts from './Charts';
import WhiteStatApi from "./WhiteStatApi";

class App {
  static init () {
    const nav = new Navigation();
    const scrollableComponents = new ScrollableComponents();
    const charts = new Charts();
    const api = new WhiteStatApi();

    api.init(charts);
    nav.init(charts);
    scrollableComponents.init();
    //charts.init(api);
  }
}

export default App;
