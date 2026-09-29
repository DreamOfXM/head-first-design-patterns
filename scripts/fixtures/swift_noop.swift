// 夹具：noop_override 的漏检护栏。前四行是四种真实写法，都必须报（同文件合成一条）；
// 后两行必须不报——不带 override 的空方法是普通实现，返回真取值的覆盖不是空覆盖。
class Animal { func sound() -> String { return "..." } func move(_ d: Int) { } }
class Dog: Animal {
    override func sound() -> String {
    }
}
class Cat: Animal { override func sound() -> String { } }
class Fish: Animal {
    override func move(_ d: Int) {}
}
class Bird: Animal { @objc override func sound() -> String { return "" } }
class Wolf: Animal { override func sound() -> String { return super.sound() + "!" } }
