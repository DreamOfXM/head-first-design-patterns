// 夹具：应当只被报出 state_field_branch / tag_switch / deep_inheritance /
// single_impl_seam / concrete_type_spread。
class PricingEngine {
    init(_ t: TaxTable) {}
}

protocol LoadingState {
    func onEnter(_ ctx: OrderCtx)
}

final class IdleState: LoadingState {
    func onEnter(_ ctx: OrderCtx) {
        ctx.reset()
    }
}

class CoreFlow {
    func tick() {}
}

class BaseFlow : CoreFlow {
    func spin() {}
}

class OrderFlow : BaseFlow {
    var state = FlowState.ready
    let engine = PricingEngine(taxTable)

    func describe() -> String {
        switch self.state {
        case .ready:
            return "ready"
        case .running:
            return "running"
        case .finished:
            return "done"
        }
    }

    func hint() -> String {
        if self.state == .ready {
            return "idle"
        }
        if state == .running {
            return "busy"
        }
        return "other"
    }
}
