/*
A KBase module: mightymorphingmodels
*/

module mightymorphingmodels {
    /*
        Insert your typespec information here.
    */
    typedef structure {
    	string workspace;
      string fbamodel_id;
      string output_id;
    } CallingParams;

    typedef structure {
      string report_name;
    	string report_ref;
    } CallingResults;

    /*
     * Morph Function
     */
     funcdef morph_model(CallingParams params) returns (CallingResults) authentication required;
};
