// 夹具：应当只被报出 tag_switch / chained_getters / global_access_point /
// cross_cutting_repeat / passthrough_class 五种形状。
export const appDeps = new AuditSink()

function priceOf(order: OrderLine): number {
  switch (order.kind) {
    case "cheese":
      return 12
    case "veggie":
      return 15
    case "clam":
      return 20
  }
  return 0
}

class InnerStore {
  read(id: string): string {
    return id
  }
}

class OrderFacade {
  inner: InnerStore

  load(id: string): string {
    return this.inner.read(id)
  }

  store(id: string): string {
    return this.inner.read(id)
  }

  erase(id: string): string {
    return this.inner.read(id)
  }

  rename(id: string): string {
    return this.inner.read(id)
  }
}

class Stats {
  logger: Logger
  a: string
  b: string
  c: string

  onFirst(id: string): void {
    this.logger.info("order seen");
    this.a = id
  }

  onSecond(id: string): void {
    this.logger.info("order seen");
    this.b = id
  }

  onThird(id: string): void {
    this.logger.info("order seen");
    this.c = id
  }
}

function report(order: Order): string {
  const deep = order.customer().address().city()
  return deep + priceOf(order.firstLine()).toString()
}
