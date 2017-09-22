/**
 * Created by maxmaguire on 3/24/17.
 */

public class Data {
    private Integer foobar = null;

    public boolean isReady() {
        return (foobar != null);
    }

    public Integer getFoobar() {
        return foobar;
    }

    public void setFoobar(Integer foobar) {
        this.foobar = foobar;
    }

    @Override
    public String toString() {
        return "Data [Foobar=" + foobar + "]";
    }
}
