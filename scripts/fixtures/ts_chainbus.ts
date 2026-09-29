// 夹具：跨行包装栈 + on/off/emit 手写派发。
// 这两处在单行正则下会给出假的"无信号"，故必须常驻夹具表。
export class EventBus {
  private map = new Map<string, Handler[]>();

  on(key: string, handler: Handler) {
    this.map.set(key, (this.map.get(key) || []).concat(handler));
  }

  off(key: string, handler: Handler) {
    this.map.set(key, (this.map.get(key) || []).filter(h => h !== handler));
  }

  emit(key: string, payload: unknown) {
    for (const handler of this.map.get(key) || []) handler(payload);
  }
}

const drink = new Mocha(
  new Mocha(
    new Soy(
      new HouseBlend())));
