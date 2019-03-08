/*
A KBase module: mightymorphingmodels
*/

module mightymorphingmodels {
    /*
        Insert your typespec information here.
    */
    typedef structure {
    	string fbamodel_workspace;
      string fbamodel_id;
      string media_workspace;
      string media_id;
      string workspace;
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
