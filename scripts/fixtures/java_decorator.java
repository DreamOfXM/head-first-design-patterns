// 夹具：应当只被报出 wrapper_chain / global_access_point。
public interface Beverage {
    int cost();

    String description();
}

public class HouseBlend implements Beverage {
    public int cost() {
        return 5;
    }

    public String description() {
        return "house blend";
    }
}

public class DarkRoast implements Beverage {
    public int cost() {
        return 8;
    }

    public String description() {
        return "dark roast";
    }
}

public class Decaf implements Beverage {
    public int cost() {
        return 3;
    }

    public String description() {
        return "decaf";
    }
}

public class Mocha implements Beverage {
    private Beverage inner;

    public Mocha(Beverage wrap) {
        this.inner = wrap;
    }

    public int cost() {
        return inner.cost() + 1;
    }

    public String description() {
        return inner.description() + ", Mocha";
    }
}

class StreamRunner {
    void run(File f) throws Exception {
        InputStream raw = new BufferedInputStream(new FileInputStream(f));
        Pricer p = Pricer.getInstance().forRegion("us");
        raw.close();
    }
}
