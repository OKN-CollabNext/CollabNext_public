import { useEffect } from "react";
import { Box } from "@chakra-ui/react";
import { ResearchDataInterface } from "../utils/interfaces";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

const createLegend = (map: L.Map) => {
  const legend = new L.Control({ position: "bottomright" });

  legend.onAdd = function () {
    const div = L.DomUtil.create("div");

    div.innerHTML = `
      <div style="
        background: rgba(255, 255, 255, 0.8); /* Semi-transparent white */
        padding: 10px;
        border-radius: 5px;
        font-size: 14px;
        color: #333;
        box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.2);
        line-height: 1.5;
        width: fit-content;
      ">
        <h4 style="margin: 0 0 5px; font-size: 16px; text-align: center;">Marker Legend</h4>
        <table style="width: 100%; border-collapse: collapse;">
          <tr>
            <td style="padding: 5px; vertical-align: middle;">
              <img src="/assets/map_markers/marker-icon-blue.png" style="width: 20px; height: 34px;" />
            </td>
            <td style="padding: 5px;">0 - 99</td>
          </tr>
          <tr>
            <td style="padding: 5px; vertical-align: middle;">
              <img src="/assets/map_markers/marker-icon-green.png" style="width: 20px; height: 34px;" />
            </td>
            <td style="padding: 5px;">100 - 999</td>
          </tr>
          <tr>
            <td style="padding: 5px; vertical-align: middle;">
              <img src="/assets/map_markers/marker-icon-violet.png" style="width: 20px; height: 34px;" />
            </td>
            <td style="padding: 5px;">1,000 - 9,999</td>
          </tr>
          <tr>
            <td style="padding: 5px; vertical-align: middle;">
              <img src="/assets/map_markers/marker-icon-orange.png" style="width: 20px; height: 34px;" />
            </td>
            <td style="padding: 5px;">10,000 - 99,999</td>
          </tr>
          <tr>
            <td style="padding: 5px; vertical-align: middle;">
              <img src="/assets/map_markers/marker-icon-red.png" style="width: 20px; height: 34px;" />
            </td>
            <td style="padding: 5px;">100,000+</td>
          </tr>
        </table>
      </div>
    `;

    return div;
  };
  legend.addTo(map);

  return legend;
};

const getMarkerIcon = (number: number) => {
  let color = "blue"; 

  if (number >= 100000) color = "red";       
  else if (number >= 10000) color = "orange"; 
  else if (number >= 1000) color = "violet";   
  else if (number >= 100) color = "green";   
  else if (number >= 0) color = "blue";     

  return L.icon({
    iconUrl: `/assets/map_markers/marker-icon-${color}.png`,
    shadowUrl: "https://unpkg.com/leaflet@1.9.3/dist/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
  });
};

const MapMetadata = ({ data }: { data: ResearchDataInterface }) => {
  useEffect(() => {
    if (!data || !data.coordinates || data.coordinates.length === 0) {
      console.error("No coordinates available in data");
      return;
    }
    const coordinates = data.coordinates;

    let map = L.map("map-container", { zoomControl: false });
    let legend: L.Control | null = null;

    map.setView([coordinates[0].lat, coordinates[0].lng], 5);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "© OpenStreetMap contributors",
    }).addTo(map);


    data.search === "topic"
    ? coordinates.forEach((coord) => {
        const matchedEntry = data.organizations.find(entry => entry[0] === coord.name);
        const number = matchedEntry ? matchedEntry[1] : "N/A";
        

        L.marker([coord.lat, coord.lng], { icon: getMarkerIcon(Number(number)) })
          .addTo(map)
          .bindPopup(`Organization: ${coord.name} <br> Number of People: ${number}`);
      })
      
    : coordinates.forEach((coord) => {
        L.marker([coord.lat, coord.lng], { icon: getMarkerIcon(0) })
          .addTo(map)
          .bindPopup(`Organization: ${coord.name} <br>Latitude: ${coord.lat} <br> Longitude: ${coord.lng}`);
      });
  
    if (data.search == "topic") legend = createLegend(map);

    return () => {
      map.remove(); 
      if (legend) legend.remove();
    };
  }, [data]);

  return (
    <Box width="100%" height="500px">
      <div id="map-container" style={{ width: "100%", height: "100%" }}></div>
    </Box>
  );
};

export default MapMetadata;
