"use client";

import mapboxgl from "mapbox-gl";
import {
  useRef,
  useState,
  useEffect,
  useCallback,
  KeyboardEventHandler,
} from "react";

import Routes from "./routes.json";
import Stops from "./stops.json";
import { Geometry, GeoJsonProperties, Feature } from "geojson";
import Image from "next/image";
import { CgArrowsExpandUpRight, CgArrowsExpandDownLeft } from "react-icons/cg";
import { AiFillCheckCircle } from "react-icons/ai";

// import ConfettiExplosion from "react-confetti-explosion";

mapboxgl.accessToken =
  "pk.eyJ1IjoibWlzZml0czA5IiwiYSI6ImNsbzA3eWFqbzA4aWUyaW55ajF1cXNzeTMifQ.w-uskgDthj4HvLLg_sUO0Q";

const normalize = (str: string) => {
  return str
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replaceAll(" ", "")
    .replaceAll("-", "");
};

export default function Home() {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const attemptInput = useRef<HTMLInputElement>(null);
  const [lng, setLng] = useState(2.349014);
  const [lat, setLat] = useState(48.864716);
  const [zoom, setZoom] = useState(11);
  const [found, setFound] = useState<string[]>([]);
  const [initialized, setInitialized] = useState<boolean>(false);
  const [footerCollapsed, setFooterCollapsed] = useState<boolean>(false);

  const updateFound = useCallback(() => {
    map.current?.setLayoutProperty("stops", "text-field", [
      "case",
      ["in", ["get", "id"], ["literal", found]],
      ["get", "name"],
      "",
    ]);
  }, [map, found]);

  const testStopAttempt = useCallback<KeyboardEventHandler<HTMLInputElement>>(
    (e) => {
      if (attemptInput.current === null) return;
      if (attemptInput.current.value === "") return;

      if (e.key !== "Enter") {
        return;
      }

      const stop_name_attempt = normalize(attemptInput.current.value);
      const match = Object.keys(Stops).find(
        (stop) => normalize(stop) === stop_name_attempt
      );

      if (match === undefined) {
        attemptInput.current.setAttribute("status", "fail");
        return;
      }
      const matchedId = (Stops as any)[match].id;
      if (found.includes(matchedId)) {
        // already found
        attemptInput.current.value = "";
        attemptInput.current.setAttribute("status", "alreadyFound");
        return;
      }

      attemptInput.current.setAttribute("status", "success");
      attemptInput.current.value = "";
      setFound([...found, matchedId]);
    },
    [map, found, setFound]
  );

  useEffect(() => {
    if (map.current === null || !map.current.loaded()) return;
    updateFound();
  }, [found, updateFound, map]);

  useEffect(() => {
    if (found.length === 0) return;
    localStorage.setItem("found", JSON.stringify(found));
  }, [found]);

  useEffect(() => {
    if (map.current) return; // initialize map only once
    map.current = new mapboxgl.Map({
      container: mapContainer.current ?? "",
      style: "mapbox://styles/misfits09/clo099i7p00ci01r27vm91puo",
      center: [lng, lat],
      zoom: zoom,
    });
    map.current.on("load", () => {
      Object.keys(Routes).forEach((route) => {
        map.current?.addSource(route, {
          type: "geojson",
          data: (Routes as any)[route].shape as string,
        });
        map.current?.addLayer({
          id: route,
          type: "line",
          source: route,
          layout: {
            "line-join": "round",
            "line-cap": "round",
          },
          paint: {
            "line-color": ("#" + (Routes as any)[route].color) as string,
            "line-width": 2,
          },
        });
      });

      const features: Array<Feature<Geometry, GeoJsonProperties>> = [];
      Object.keys(Stops).forEach((stop_name) => {
        const stop_data = (Stops as any)[stop_name] as any;
        features.push({
          type: "Feature",
          geometry: {
            type: "Point",
            coordinates: stop_data.coords,
          },
          properties: {
            name: stop_name,
            id: stop_data.id,
          },
        });
      });
      map.current?.addSource("stops", {
        type: "geojson",
        data: {
          type: "FeatureCollection",
          features: features,
        },
      });

      let foundLocal: string[] | null = null;
      const foundString = localStorage.getItem("found");
      if (foundString !== null) {
        const foundFromStorage = JSON.parse(foundString) as string[];
        if (
          foundFromStorage.length > 0 &&
          confirm("Souhaitez vous reprendre la partie en cours ?")
        ) {
          foundLocal = foundFromStorage;
        }
        localStorage.removeItem("found");
      }

      map.current?.loadImage("/dot.png", (error, image) => {
        if (error) throw error;
        if (image === undefined) throw new Error("image is undefined");
        map.current?.addImage("stop-dot", image);
        map.current?.addLayer({
          id: "stops",
          type: "symbol",
          source: "stops", // reference the data source
          paint: {
            "text-halo-color": "#fff",
            "text-halo-width": 2,
          },
          layout: {
            "text-field": [
              "case",
              ["in", ["get", "id"], ["literal", foundLocal ?? found]],
              ["get", "name"],
              "",
            ],
            "text-size": ["interpolate", ["linear"], ["zoom"], 14, 10, 15, 14],
            "text-offset": [0, 1],
            "icon-image": "stop-dot", // reference the image
            "icon-size": [
              "interpolate",
              ["linear"],
              ["zoom"],
              14,
              0.015,
              15,
              0.03,
            ],
          },
        });
      });

      if (foundLocal != null) setFound(foundLocal);
      setInitialized(true);
    });
  });

  return (
    <main className="flex flex-col items-center justify-between">
      <div className="header">
        <h1 className="title">Quiz - Les transports en île de france</h1>
        <p className="score">
          {((100 * found.length) / Object.keys(Stops).length).toFixed(2)}%
        </p>
        <input
          placeholder="Proposition..."
          type="text"
          ref={attemptInput}
          onKeyUp={testStopAttempt}
          disabled={!initialized}
          autoComplete="off"
        />
      </div>
      <div className="game">
        <div ref={mapContainer} className="map-container" />
      </div>
      <footer className={footerCollapsed ? "routes collapsed" : "routes"}>
        <div
          className="collapse-btn"
          onClick={() => setFooterCollapsed(!footerCollapsed)}
        >
          {footerCollapsed ? (
            <span>
              <CgArrowsExpandUpRight />
            </span>
          ) : (
            <span>
              <CgArrowsExpandDownLeft />
            </span>
          )}
        </div>
        {Object.keys(Routes).map((route) => {
          const foundStops = (
            (Routes as any)[route].stops as Array<string>
          ).filter((stop) => found.includes(stop)).length;
          const totalStops = ((Routes as any)[route].stops as Array<string>)
            .length;

          return (
            <div
              key={route}
              className={foundStops == totalStops ? "route complete" : "route"}
            >
              <Image
                src={(Routes as any)[route].logo}
                alt={(Routes as any)[route].name}
                width={20}
                height={20}
                className="route-logo"
              />
              {foundStops < totalStops ? (
                <p className="route-score">
                  {((100 * foundStops) / totalStops).toFixed(0)}%
                </p>
              ) : (
                <div className="check">
                  <AiFillCheckCircle
                    style={{ color: "#0d0", height: "100%", width: "100%" }}
                  />
                </div>
              )}
            </div>
          );
        })}
      </footer>
    </main>
  );
}
