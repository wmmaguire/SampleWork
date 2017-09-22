/**
 * This is a class to hold class grade information
 * @author maxmaguire
 *
 */
public class FinalData implements Comparable<FinalData> {
    /**
     * Instance variable for year.
     */
    private int year;
    /**
     * Instance variable for semester.
     */
    private String semester;
    /**
     * Instance variable for Amount.
     */
    private String courseName;
    /**
     * Instance variable for candidate.
     */
    private int units;
    /**
     * Instance variable for grade.
     */
    private String grade;
    /**
     * Instance variable for Amount.
     */
    private float points;

    /**
     * Constructs object with Last Name,First Name, Amount.
     * @param andrewId object.
     */
    public FinalData(int yearEntry, String semesterEntry, String courseNameEntry, 
            int unitEntry, String gradeEntry) {
        grade      = gradeEntry;
        courseName = courseNameEntry;
        units      = unitEntry;
        semester   = semesterEntry;
        year       = yearEntry;
        points     = computeClassPoints();
    }
    /**
     * Returns year of object.
     * @return year.
     */
    public int getYear() {
        return year;
    }
    /**
     * Returns semester for object.
     * @return semester.
     */
    public String getSemester() {
        return semester;
    }
    /**
     * Returns course name of object.
     * @return course name.
     */
    public String getCourseName() {
        return courseName;
    }
    /**
     * Returns course Units of object.
     * @return course units.
     */
    public int getUnits() {
        return units;
    }
    /**
     * Returns grade of object.
     * @return grade.
     */
    public String getGrade() {
        return grade;
    }
    /**
     * Returns Points of object.
     * @return points.
     */
    public float computeClassPoints() {
        float ptEntry = units*this.retrieveNumGrade();
        return ptEntry;
    }
    /**
     * Returns points of object.
     * @return lastName.
     */
    public double getPoints() {
        return points;
    }
    private float retrieveNumGrade() {
        //for (int i = 0; )
       // float[] numval = {4,3,2,1,0};
        if(grade.equals("A")){
            return (float)4.0;        
        }
        if(grade.equals("B")){
            return (float)3.0;        
        }
        if(grade.equals("C")){
            return (float)2.0;        
        }
        if(grade.equals("D")){
            return (float)1.0;        
        }
        if(grade.equals("F")){
            return (float)0.0;        
        }
        return (float)0.0;
    }
    @Override
    public String toString() {
        String result = (String.format(" %-7s %-7s  %-38s  %-10s %10s %10s",
                year,semester,courseName,units,grade,points));
        return result;
    }
    @Override
    public int compareTo(FinalData o) {
        Integer c1_year = this.getYear();
        Integer c2_year = o.getYear();
        if (c2_year.equals(c1_year)) {
            String c2_sem = this.semester;
            String c1_sem = o.semester;
            if (c2_sem.equals(c1_sem)) {
                String c2_cName = this.getCourseName();
                String c1_cName = o.getCourseName();
                return c2_cName.compareTo(c1_cName);
            }
            return c2_sem.compareTo(c1_sem);
        }
        return c2_year.compareTo(c1_year);
    }     
}
