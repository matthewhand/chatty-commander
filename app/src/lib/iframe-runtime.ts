import { createBus } from './bus';

const bus = createBus(window.parent);

bus.post('canvas:ready');

export default bus;

