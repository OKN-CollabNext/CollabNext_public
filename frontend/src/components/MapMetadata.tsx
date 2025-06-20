import { useEffect, useRef, useState } from "react";
import { Box, Spinner, Center } from "@chakra-ui/react";
import { ResearchDataInterface } from "../utils/interfaces";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { baseUrl } from "../utils/constants";

const createLegend = (map: L.Map) => {
  const legend = new L.Control({ position: "bottomright" });

  legend.onAdd = function () {
    const div = L.DomUtil.create("div");
    div.innerHTML = `
      <div style="
        background: rgba(255, 255, 255, 0.8);
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
          <tr><td><img src="/assets/map_markers/marker-icon-blue.png" style="width: 20px; height: 34px;" /></td><td>0 - 99</td></tr>
          <tr><td><img src="/assets/map_markers/marker-icon-green.png" style="width: 20px; height: 34px;" /></td><td>100 - 999</td></tr>
          <tr><td><img src="/assets/map_markers/marker-icon-violet.png" style="width: 20px; height: 34px;" /></td><td>1,000 - 9,999</td></tr>
          <tr><td><img src="/assets/map_markers/marker-icon-orange.png" style="width: 20px; height: 34px;" /></td><td>10,000 - 99,999</td></tr>
          <tr><td><img src="/assets/map_markers/marker-icon-red.png" style="width: 20px; height: 34px;" /></td><td>100,000+</td></tr>
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

  return L.icon({
    iconUrl: `/assets/map_markers/marker-icon-${color}.png`,
    shadowUrl: "https://unpkg.com/leaflet@1.9.3/dist/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
  });
};

const MapMetadata = ({ data }: { data: ResearchDataInterface }) => {
  const mapRef = useRef<L.Map | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!data?.coordinates?.length) {
      console.error("No coordinates in data");
      setLoading(false);
      return;
    }
    const fetchAndRenderMap = async () => {
      setLoading(true);

      const institutions = data.coordinates;

      let coordinates: {
        lat: number;
        lng: number;
        name: string;
        authors: number;
      }[] = [];

      try {
        const res = await fetch(`${baseUrl}/geo_info_batch`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ institutions }),
        });

        coordinates = await res.json();
      } catch (error) {
        console.error("Failed to fetch batched geo info", error);
        setLoading(false);
        return;
      }

      if (!coordinates.length) {
        setLoading(false);
        return;
      }

      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }

      const container = L.DomUtil.get("map-container");
      if (container && (container as any)._leaflet_id) {
        (container as any)._leaflet_id = undefined;
      }

      const map = L.map("map-container", { zoomControl: false }).setView(
        [coordinates[0].lat, coordinates[0].lng],
        5
      );
      mapRef.current = map;

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "© OpenStreetMap contributors",
      }).addTo(map);

      coordinates.forEach(({ lat, lng, name, authors }) => {
        L.marker([lat, lng], {
          icon: getMarkerIcon(authors),
        })
          .addTo(map)
          .bindPopup(`Organization: ${name}<br>Authors: ${authors}`);
      });

      createLegend(map);
      setLoading(false);
    };

    fetchAndRenderMap();

    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, [data]);

  return (
    <Box width="100%" height="500px" position="relative">
      {loading && (
        <Center
          position="absolute"
          width="100%"
          height="100%"
          top={0}
          left={0}
          zIndex={10}
          background="rgba(255,255,255,0.6)"
        >
          <Spinner size="xl" thickness="4px" speed="0.65s" color="blue.500" />
        </Center>
      )}
      <div id="map-container" style={{ width: "100%", height: "100%" }} />
    </Box>
  );
};

export default MapMetadata;
