package com.example.maxmaguire.myparticlephotonapp;

/**
 * Created by maxmaguire on 3/24/17.
 */

public class Data {
    private String foobar = null;
    private int value = 0;

    public boolean isReady() {
        return (foobar != null);
    }

    public String getData() {
        return foobar;
    }
    public int getValue() {
        return value;
    }

    public void setData(String foobar, int inputVal) {
        this.foobar = foobar;
        this.value = inputVal;
    }

    @Override
    public String toString() {
        return "Data [Foobar=" + foobar + "]";
    }
}
