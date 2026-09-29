// 夹具：与 swift_state.swift 共同构造 PricingEngine，用于跨文件 spread 判定。
// 本文件自身不应产生任何信号——它同时也是 spread/state/链式三项的假阳性回归护栏：
// 值类型构造、初始化标签 `state: state,`、按状态做数据筛选、行首点的 SwiftUI 修饰链。
struct Row {
    var state: SessionState = .resting
    var title: String
}

final class TwinRunner {
    func build(taxTable: TaxTable, rows: [Row]) -> PricingEngine {
        let restingCount = rows.filter { $0.state == .resting }.count
        let engine = PricingEngine(taxTable)
        commit(title: rows.first?.title ?? "", state: state, count: restingCount)
        return engine
    }
}

extension TwinRunner {
    var label: String {
        return Text("ping")
            .font(Theme.mono).foregroundColor(Theme.ink2).opacity(0.72)
            .padding(6)
    }
}
